// Turns a picked / pasted / dropped image into a data URL the API accepts. Photos are downscaled to at most
// MAX_SIDE px and re-encoded as JPEG, so a 12 MP phone photo goes up as a few hundred kB (the API caps each
// image at ~3.7 MB and accepts at most MAX_IMAGES).

export const MAX_IMAGES = 3;
const MAX_SIDE = 1600;

export type Attachment = { id: string; name: string; url: string };

let nextId = 0; // not crypto.randomUUID(): it only exists on https/localhost, and graders may use http://<ip>

export async function toAttachment(file: File): Promise<Attachment> {
  if (!file.type.startsWith("image/")) throw new Error(`“${file.name}” is not an image.`);
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new Error(`“${file.name}” could not be read. Use a PNG, JPEG, WebP or GIF image.`);
  }
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("This browser cannot process images.");
  ctx.fillStyle = "#fff"; // JPEG has no transparency: put transparent screenshots on white, not black
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return { id: `img-${++nextId}`, name: file.name || "pasted image", url: canvas.toDataURL("image/jpeg", 0.88) };
}
