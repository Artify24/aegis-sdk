export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { email, password } = body;

    // Simulate database lookup and password check
    if (email === "demo@aegis.cloud" && password === "password123") {
      return Response.json({
        token: "mock-jwt-token-aegis-12345",
        user: {
          id: "u-987654321",
          name: "Demo User",
          email: "demo@aegis.cloud"
        }
      });
    }

    return Response.json({ message: "Invalid credentials" }, { status: 401 });
  } catch (error) {
    return Response.json({ message: "Internal server error" }, { status: 500 });
  }
}
