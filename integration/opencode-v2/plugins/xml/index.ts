import { Plugin } from "@opencode/plugin"
import { spawnSync } from "child_process"
import * as fs from "fs"
import * as os from "os"
import * as path from "path"

const MAX_BUFFER = 10 * 1024 * 1024

function extractErrorDetail(stderr: string): string {
  const lines = stderr.split(/\r?\n/).map((line) => line.trimEnd())
  const nonEmpty = lines.filter((line) => line.trim() !== "")
  const tracebackStart = lines.findIndex((line) => line.startsWith("Traceback"))
  if (tracebackStart !== -1) {
    return nonEmpty[nonEmpty.length - 1] ?? "Unknown error"
  }
  let detail: string[] | null = null
  for (let i = 0; i < nonEmpty.length; i++) {
    if (nonEmpty[i].includes("error:")) {
      detail = nonEmpty.slice(i).map((line) => line.replace(/^.*?: error: /, ""))
      break
    }
  }
  return (detail ?? nonEmpty).join("\n")
}

function runTool(command: string, args: string[], cwd: string): string {
  const result = spawnSync(command, args, { cwd, encoding: "utf8", maxBuffer: MAX_BUFFER })
  if (result.error) return `Error: ${result.error.message}`
  const stderr = result.stderr ?? ""
  const stdout = result.stdout ?? ""
  if (result.status !== 0) {
    const detail = stderr.trim() !== "" ? extractErrorDetail(stderr) : stdout.trim() || "no output"
    return `Error (exit code ${result.status ?? "signal"}): ${detail}`
  }
  if (stderr.trim() !== "") {
    return `${normalize(stdout)}\nstderr: ${extractErrorDetail(stderr)}`
  }
  return normalize(stdout)
}

function normalize(text: string): string {
  return text.replace(/\r\n/g, "\n").trimEnd()
}

export default Plugin.define({
  id: "xml-xsl-tools",
  setup(ctx) {
    const directory = ctx.location.directory

    ctx.tool.transform((tools) => {
      tools.add({
        name: "xml_query",
        description: "Extract data from XML files using XPath. Use when querying or extracting data from XML.",
        input: {
          type: "object",
          properties: {
            xpath: {
              type: "string",
              description:
                "XPath expression (must start with / or (). Use //elem/text() for text content, (//elem)[n] for first n globally).",
            },
            xmlFile: { type: "string", description: "Path to XML file." },
          },
          required: ["xpath", "xmlFile"],
          additionalProperties: false,
        },
        async execute(input) {
          const { xpath, xmlFile } = input as { xpath?: string; xmlFile?: string }
          if (!xpath) return { content: "Error: xpath is required" }
          if (!xmlFile) return { content: "Error: xmlFile is required" }
          return { content: runTool("xpe", [xpath, xmlFile], directory) }
        },
      })

      tools.add({
        name: "xml_transform",
        description: "Transform XML files using XSLT 1.0 stylesheets.",
        input: {
          type: "object",
          properties: {
            stylesheet: { type: "string", description: "Path to XSL file, or inline XSLT content." },
            xmlFile: { type: "string", description: "Path to XML file." },
            params: {
              type: "array",
              items: { type: "string" },
              description: "XSLT parameters as NAME=VALUE pairs (e.g. ['limit=10', 'name=foo']).",
            },
          },
          required: ["stylesheet", "xmlFile"],
          additionalProperties: false,
        },
        async execute(input) {
          const { stylesheet, xmlFile, params } = input as {
            stylesheet?: string
            xmlFile?: string
            params?: string[]
          }
          if (!stylesheet) return { content: "Error: stylesheet is required" }
          if (!xmlFile) return { content: "Error: xmlFile is required" }

          const isInline = stylesheet.trim().startsWith("<")

          let stylesheetPath = stylesheet
          let tempFile: string | null = null

          if (isInline) {
            tempFile = path.join(os.tmpdir(), `xte-${Date.now()}.xsl`)
            fs.writeFileSync(tempFile, stylesheet, "utf8")
            stylesheetPath = tempFile
          }

          try {
            const argv = [stylesheetPath, xmlFile]
            for (const param of params ?? []) {
              argv.push("-p", param)
            }
            return { content: runTool("xte", argv, directory) }
          } finally {
            if (tempFile) {
              try {
                fs.unlinkSync(tempFile)
              } catch {}
            }
          }
        },
      })

      tools.add({
        name: "xml_validate",
        description: "Validate XML files against XSD schemas.",
        input: {
          type: "object",
          properties: {
            schema: { type: "string", description: "Path to XSD schema file." },
            xmlFile: { type: "string", description: "Path to XML file." },
          },
          required: ["schema", "xmlFile"],
          additionalProperties: false,
        },
        async execute(input) {
          const { schema, xmlFile } = input as { schema?: string; xmlFile?: string }
          if (!schema) return { content: "Error: schema is required" }
          if (!xmlFile) return { content: "Error: xmlFile is required" }
          const result = runTool("xve", [schema, xmlFile], directory)
          return { content: result === "" ? "Validation passed" : result }
        },
      })
    })
  },
})
