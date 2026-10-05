import {
  NextRequest,
  NextResponse,
} from "next/server";

const AUTH_COOKIE_NAME =
  "mines_admin_token";

export function proxy(
  request: NextRequest
) {
  const { pathname } =
    request.nextUrl;

  const token =
    request.cookies.get(
      AUTH_COOKIE_NAME
    )?.value;

  // Login page
  if (pathname === "/login") {
    if (token) {
      return NextResponse.redirect(
        new URL(
          "/dashboard",
          request.url
        )
      );
    }

    return NextResponse.next();
  }

  // Allow Next.js internals and static files
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Protect application pages
  if (!token) {
    return NextResponse.redirect(
      new URL(
        `/login?redirect=${encodeURIComponent(pathname)}`,
        request.url
      )
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};