import { tool } from "@opencode-ai/plugin"
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

export const query = tool({
  description: "Extract data from XML files using XPath. Use when querying or extracting data from XML.",
  args: {
    xpath: tool.schema.string().describe("XPath expression (must start with / or (). Use //elem/text() for text content, (//elem)[n] for first n globally)."),
    xmlFile: tool.schema.string().describe("Path to XML file."),
  },
  async execute(args, context) {
    if (!args.xpath) return "Error: xpath is required"
    if (!args.xmlFile) return "Error: xmlFile is required"
    return runTool("xpe", [args.xpath, args.xmlFile], context.directory)
  },
})

export const transform = tool({
  description: "Transform XML files using XSLT 1.0 stylesheets.",
  args: {
    stylesheet: tool.schema.string().describe("Path to XSL file, or inline XSLT content."),
    xmlFile: tool.schema.string().describe("Path to XML file."),
    params: tool.schema.array(tool.schema.string()).optional().describe("XSLT parameters as NAME=VALUE pairs (e.g. ['limit=10', 'name=foo'])."),
  },
  async execute(args, context) {
    if (!args.stylesheet) return "Error: stylesheet is required"
    if (!args.xmlFile) return "Error: xmlFile is required"

    const isInline = args.stylesheet.trim().startsWith("<")

    let stylesheetPath = args.stylesheet
    let tempFile: string | null = null

    if (isInline) {
      tempFile = path.join(os.tmpdir(), `xte-${Date.now()}.xsl`)
      fs.writeFileSync(tempFile, args.stylesheet, "utf8")
      stylesheetPath = tempFile
    }

    try {
      const argv = [stylesheetPath, args.xmlFile]
      for (const param of args.params ?? []) {
        argv.push("-p", param)
      }
      return runTool("xte", argv, context.directory)
    } finally {
      if (tempFile) {
        try { fs.unlinkSync(tempFile) } catch {}
      }
    }
  },
})

export const validate = tool({
  description: "Validate XML files against XSD schemas.",
  args: {
    schema: tool.schema.string().describe("Path to XSD schema file."),
    xmlFile: tool.schema.string().describe("Path to XML file."),
  },
  async execute(args, context) {
    if (!args.schema) return "Error: schema is required"
    if (!args.xmlFile) return "Error: xmlFile is required"
    const result = runTool("xve", [args.schema, args.xmlFile], context.directory)
    return result === "" ? "Validation passed" : result
  },
})
