/** Copy text, through Electron where we have it: the browser clipboard API
 * is missing on the file:// page the packaged app loads. */
export async function copyText(text: string): Promise<void> {
  try {
    const { clipboard } = require("electron");
    clipboard.writeText(text);
  } catch (e) {
    await navigator.clipboard.writeText(text);
  }
}
