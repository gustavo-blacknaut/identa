import { NextResponse, type NextRequest } from "next/server";

const PUBLIC_PREFIXES = ["/entrar", "/configuracao-inicial", "/convite/", "/verificar-email/", "/redefinir-senha", "/enviar/"];
const SESSION_COOKIES = ["identa_session", "identa_refresh"];

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  if (PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) return NextResponse.next();
  if (SESSION_COOKIES.some((name) => request.cookies.has(name))) return NextResponse.next();
  const target = new URL("/entrar", request.url);
  if (pathname !== "/" && pathname !== "/pessoas") target.searchParams.set("next", pathname + search);
  return NextResponse.redirect(target);
}

export const config = {
  matcher: ["/((?!api|health|_next/static|_next/image|favicon.svg|.*\.(?:svg|png|webp|ico|txt)$).*)"],
};
