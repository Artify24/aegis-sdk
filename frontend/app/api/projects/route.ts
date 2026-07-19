import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export async function GET() {
  const projects = await db.projects.findMany();
  // Sort descending by created at for consistency
  projects.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  return NextResponse.json(projects);
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const newProj = await db.projects.create(body);
    return NextResponse.json(newProj, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: "Failed to create project" }, { status: 400 });
  }
}
