import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const execution = await db.executions.findById(id);
  
  if (!execution) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  return NextResponse.json(execution);
}
