// ============================================================
// ESRGAN API Route - Proxy to Backend
// ============================================================

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// ============================================================
// POST /api/esrgan/upscale - Upload and upscale image
// ============================================================

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint") || "upscale";

  try {
    // Get the form data from the client request
    const formData = await request.formData();

    // Forward the request to the backend
    const response = await fetch(`${BACKEND_URL}/${endpoint}`, {
      method: "POST",
      body: formData,
    });

    // Get the response data
    const data = await response.json();

    // Return the response
    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || "Backend request failed" },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("API route error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}

// ============================================================
// GET /api/esrgan/* - Proxy GET requests
// ============================================================

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint") || "health";

  try {
    const response = await fetch(`${BACKEND_URL}/${endpoint}`);
    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || "Backend request failed" },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("API route error:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}
