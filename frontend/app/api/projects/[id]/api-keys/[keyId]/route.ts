import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string, keyId: string }> }) {
  const { keyId } = await params;
  try {
    const data = await req.json();
    const updated = await db.apiKeys.update(keyId, data);
    if (!updated) return NextResponse.json({ error: "Not found" }, { status: 404 });
    const { key, ...safe } = updated;
    return NextResponse.json(safe);
  } catch (error) {
    return NextResponse.json({ error: "Failed to update" }, { status: 400 });
  }
}

export async function DELETE(req: Request, { params }: { params: Promise<{ id: string, keyId: string }> }) {
  const { keyId } = await params;
  await db.apiKeys.delete(keyId);
  return new NextResponse(null, { status: 204 });
}
