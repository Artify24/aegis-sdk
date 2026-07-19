import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const keys = await db.apiKeys.findManyByProjectId(id);
  // Don't send full key in GET requests for security, only masked
  const safeKeys = keys.map(({ key, ...safe }) => safe);
  return NextResponse.json(safeKeys);
}

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const { name } = await req.json();
    const newKey = await db.apiKeys.create(id, name || "New Key");
    return NextResponse.json(newKey, { status: 201 }); // Only time full key is returned
  } catch (error) {
    return NextResponse.json({ error: "Failed to create API key" }, { status: 400 });
  }
}
