import * as path from "path"

// Shared test harness for both OpenCode plugin generations.
//
// The plugins resolve `@opencode*/plugin` from their own directory tree, so we
// register a Bun resolve hook that points those imports at the packages
// installed next to this harness. Resolution happens before the hook is
// registered, which keeps Bun.resolveSync from recursing into the hook.
const v1PluginEntry = Bun.resolveSync("@opencode-ai/plugin", import.meta.dir)
const v2PluginEntry = Bun.resolveSync("@opencode/plugin", import.meta.dir)

Bun.plugin({
  name: "opencode-plugin-test-resolution",
  setup(build) {
    build.onResolve({ filter: /^@opencode-ai\/plugin$/ }, () => ({ path: v1PluginEntry }))
    build.onResolve({ filter: /^@opencode\/plugin$/ }, () => ({ path: v2PluginEntry }))
  },
})

type ToolInput = Record<string, unknown>
type ToolOutput = string | { content: string }

interface Tools {
  query: (input: ToolInput) => Promise<ToolOutput>
  transform: (input: ToolInput) => Promise<ToolOutput>
  validate: (input: ToolInput) => Promise<ToolOutput>
}

interface LoadedBackend {
  tools: Tools
  toolNames: string[]
  descriptions: Record<string, string>
}

const fixtureDir = process.argv[2]
const backendName = process.argv[3] ?? "v1"

if (!fixtureDir) {
  console.error("usage: bun harness.ts <fixture-dir> [v1|v2]")
  process.exit(2)
}

function fixture(name: string): string {
  return path.join(fixtureDir, name)
}

const inlineStylesheet = [
  '<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">',
  '  <xsl:output method="text"/>',
  '  <xsl:param name="prefix"/>',
  '  <xsl:template match="/root">',
  "    <xsl:for-each select=\"item\">",
  '      <xsl:value-of select="$prefix"/><xsl:value-of select="@id"/><xsl:text>&#10;</xsl:text>',
  "    </xsl:for-each>",
  "  </xsl:template>",
  "</xsl:stylesheet>",
].join("\n")

async function loadV1(): Promise<LoadedBackend> {
  const module = await import("../../integration/opencode/xml")
  const context = {
    directory: fixtureDir,
    sessionID: "harness",
    messageID: "harness",
    agent: "harness",
    abort: new AbortController().signal,
  }
  return {
    tools: {
      query: (input) => module.query.execute(input, context),
      transform: (input) => module.transform.execute(input, context),
      validate: (input) => module.validate.execute(input, context),
    },
    toolNames: ["xml_query", "xml_transform", "xml_validate"],
    descriptions: {
      xml_query: module.query.description,
      xml_transform: module.transform.description,
      xml_validate: module.validate.description,
    },
  }
}

async function loadV2(): Promise<LoadedBackend> {
  const module = await import("../../integration/opencode-v2/plugins/xml/index")

  interface RegisteredTool {
    name: string
    description: string
    input: unknown
    execute(input: ToolInput): Promise<{ content: string }>
  }

  const registered: RegisteredTool[] = []
  const context = {
    location: { directory: fixtureDir },
    tool: {
      transform(register: (editor: { add(tool: RegisteredTool): void }) => void) {
        register({ add: (tool) => registered.push(tool) })
      },
    },
  }

  await module.default.setup(context)

  const toolsByName = new Map(registered.map((tool) => [tool.name, tool]))
  const get = (name: string) => {
    const tool = toolsByName.get(name)
    if (!tool) throw new Error(`plugin did not register ${name}`)
    return (input: ToolInput) => tool.execute(input)
  }

  return {
    tools: {
      query: get("xml_query"),
      transform: get("xml_transform"),
      validate: get("xml_validate"),
    },
    toolNames: registered.map((tool) => tool.name),
    descriptions: Object.fromEntries(registered.map((tool) => [tool.name, tool.description])),
  }
}

function unwrap(result: ToolOutput): string {
  if (typeof result === "string") return result
  if (result && typeof result === "object" && typeof result.content === "string") return result.content
  return JSON.stringify(result)
}

// Exercises the same behaviour matrix for both plugin generations so that the
// legacy V1 tools and the V2 plugin cannot drift apart unnoticed.
function caseMatrix(tools: Tools): Array<[string, () => Promise<ToolOutput>]> {
  return [
    ["query invalid xml", () => tools.query({ xpath: "//bad[[xpath", xmlFile: fixture("malformed.xml") })],
    ["query missing file", () => tools.query({ xpath: "//item/@id", xmlFile: fixture("does-not-exist.xml") })],
    ["query empty xpath", () => tools.query({ xpath: "", xmlFile: fixture("tiny.xml") })],
    ["query missing xmlFile", () => tools.query({ xpath: "//item/@id", xmlFile: "" })],
    ["query success", () => tools.query({ xpath: "//item/@id", xmlFile: fixture("tiny.xml") })],
    [
      "transform invalid stylesheet",
      () => tools.transform({ stylesheet: '<xsl:stylesheet version="1.0"><not-valid', xmlFile: fixture("tiny.xml") }),
    ],
    [
      "transform success with params",
      () => tools.transform({ stylesheet: inlineStylesheet, xmlFile: fixture("tiny.xml"), params: ["prefix=P-"] }),
    ],
    ["transform missing stylesheet", () => tools.transform({ stylesheet: "", xmlFile: fixture("tiny.xml") })],
    ["transform missing xmlFile", () => tools.transform({ stylesheet: inlineStylesheet, xmlFile: "" })],
    ["validate malformed xml", () => tools.validate({ schema: fixture("tiny.xsd"), xmlFile: fixture("malformed.xml") })],
    ["validate schema violation", () => tools.validate({ schema: fixture("tiny.xsd"), xmlFile: fixture("wrong-elem.xml") })],
    ["validate success", () => tools.validate({ schema: fixture("tiny.xsd"), xmlFile: fixture("tiny.xml") })],
    ["validate missing schema", () => tools.validate({ schema: "", xmlFile: fixture("tiny.xml") })],
    ["validate missing xmlFile", () => tools.validate({ schema: fixture("tiny.xsd"), xmlFile: "" })],
  ]
}

async function main() {
  const loaders: Record<string, () => Promise<LoadedBackend>> = { v1: loadV1, v2: loadV2 }
  const load = loaders[backendName]
  if (!load) {
    console.error(`unknown backend: ${backendName}`)
    process.exit(2)
  }

  const backend = await load()
  console.log(JSON.stringify({ type: "meta", backend: backendName, tools: backend.toolNames, descriptions: backend.descriptions }))

  for (const [name, run] of caseMatrix(backend.tools)) {
    try {
      console.log(JSON.stringify({ type: "case", case: name, result: unwrap(await run()) }))
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      console.log(JSON.stringify({ type: "case", case: name, result: `THREW: ${message}` }))
    }
  }
}

main()
