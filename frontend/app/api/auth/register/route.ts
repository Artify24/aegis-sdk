export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { name, email, password } = body;

    if (!name || !email || !password) {
      return Response.json({ message: "Missing fields" }, { status: 400 });
    }

    return Response.json({
      token: "mock-jwt-token-aegis-12345",
      user: {
        id: `u-${Math.floor(Math.random() * 1000000)}`,
        name,
        email
      }
    });
  } catch (error) {
    return Response.json({ message: "Internal server error" }, { status: 500 });
  }
}
