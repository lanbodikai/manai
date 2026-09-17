import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
async function scan(dir) {
  for (const item of await readdir(dir, { withFileTypes: true })) {
    const file = path.join(dir, item.name);
    if (item.isDirectory()) await scan(file);
    else if (file.endsWith(".js")) {
      const content = await readFile(file, "utf8");
      for (const marker of [
        "MANAI_MOCK_ONLY",
        "synthetic-fixture-v1",
        "synthetic-audit-001",
        "Original synthetic test jobs",
      ]) {
        if (content.includes(marker))
          throw new Error(`Mock payload leaked into ${file}: ${marker}`);
      }
    }
  }
}
await scan("dist");
console.log(
  "PASS: live production assets exclude mock implementation and fixture markers.",
);
