import { tool } from "@opencode-ai/plugin"

export const query = tool({
  description: "Extract data from XML files using XPath. Use when querying or extracting data from XML.",
  args: {
    xpath: tool.schema.string().describe("XPath expression (must start with / or (). Use //elem/text() for text content, (//elem)[n] for first n globally)."),
    xmlFile: tool.schema.string().optional().describe("Path to XML file. Omit to read from stdin."),
  },
  async execute(args, context) {
    const fs = require("fs")
    const { execSync } = require("child_process")
    if (!args.xpath) return "Error: xpath is required"
    const cmd = args.xmlFile
      ? `xpe "${args.xpath}" "${args.xmlFile}"`
      : `xpe "${args.xpath}"`
    return execSync(cmd, { cwd: context.directory, encoding: "utf8", maxBuffer: 10 * 1024 * 1024 })
  },
})

export const transform = tool({
  description: "Transform XML files using XSLT 1.0 stylesheets.",
  args: {
    stylesheet: tool.schema.string().describe("Path to XSL file, or inline XSLT content."),
    xmlFile: tool.schema.string().optional().describe("Path to XML file. Omit to read from stdin."),
    params: tool.schema.array(tool.schema.string()).optional().describe("XSLT parameters as NAME=VALUE pairs (e.g. ['limit=10', 'name=foo'])."),
  },
  async execute(args, context) {
    const { execSync } = require("child_process")
    const fs = require("fs")
    const path = require("path")
    const os = require("os")
    
    if (!args.stylesheet) return "Error: stylesheet is required"
    const isInline = args.stylesheet.trim().startsWith("<")
    
    let stylesheetPath = args.stylesheet
    let tempFile: string | null = null
    
    if (isInline) {
      tempFile = path.join(os.tmpdir(), `xte-${Date.now()}.xsl`)
      fs.writeFileSync(tempFile, args.stylesheet, "utf8")
      stylesheetPath = tempFile
    }
    
    try {
      let cmd = `xte "${stylesheetPath}"`
      if (args.xmlFile) cmd += ` "${args.xmlFile}"`
      if (args.params && args.params.length > 0) {
        cmd += " " + args.params.map(p => `-p ${p}`).join(" ")
      }
      return execSync(cmd, { cwd: context.directory, encoding: "utf8", maxBuffer: 10 * 1024 * 1024 })
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
    xmlFile: tool.schema.string().optional().describe("Path to XML file. Omit to read from stdin."),
  },
  async execute(args, context) {
    const { execSync } = require("child_process")
    if (!args.schema) return "Error: schema is required"
    const cmd = args.xmlFile
      ? `xve "${args.schema}" "${args.xmlFile}"`
      : `xve "${args.schema}"`
    const result = execSync(cmd, { cwd: context.directory, encoding: "utf8", maxBuffer: 10 * 1024 * 1024 })
    return result || "Validation passed"
  },
})