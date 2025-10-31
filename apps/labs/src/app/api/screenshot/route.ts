import { NextResponse } from "next/server";
import { chromium } from "playwright";

export const runtime = "nodejs";

function buildShareUrl(requestUrl: URL, slug: string, params: URLSearchParams) {
  const shareParams = new URLSearchParams();
  ["metric", "cycle", "asOf"].forEach((key) => {
    const value = params.get(key);
    if (value) {
      shareParams.set(key, value);
    }
  });

  const sharePath = shareParams.size
    ? `/share/${slug}?${shareParams.toString()}`
    : `/share/${slug}`;

  const origin =
    process.env.NEXT_PUBLIC_LABS_BASE_URL ?? requestUrl.origin ?? "http://localhost:3000";

  return new URL(sharePath, origin).toString();
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const slug = url.searchParams.get("slug");

  if (!slug) {
    return NextResponse.json(
      { error: "Missing slug parameter" },
      { status: 400 }
    );
  }

  const width = Number(url.searchParams.get("width")) || 1200;
  const height = Number(url.searchParams.get("height")) || 675;

  const targetUrl = buildShareUrl(url, slug, url.searchParams);

  let browser;
  try {
    browser = await chromium.launch({
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    });

    const page = await browser.newPage({
      viewport: { width, height },
      deviceScaleFactor: 2,
    });

    await page.goto(targetUrl, { waitUntil: "networkidle" });
    await page.waitForTimeout(500);

    const screenshot = await page.screenshot({
      type: "png",
      fullPage: false,
    });

    let buffer: Buffer;
    if (typeof screenshot === "string") {
      buffer = Buffer.from(screenshot, "base64");
    } else if (screenshot instanceof ArrayBuffer) {
      buffer = Buffer.from(screenshot);
    } else {
      buffer = screenshot;
    }

    const body = buffer.buffer.slice(
      buffer.byteOffset,
      buffer.byteOffset + buffer.byteLength
    );

    return new NextResponse(body, {
      status: 200,
      headers: {
        "Content-Type": "image/png",
        "Cache-Control": "public, max-age=60",
      },
    });
  } catch (error) {
    console.error("[screenshot] failed", error);
    return NextResponse.json(
      { error: "Failed to generate screenshot" },
      { status: 500 }
    );
  } finally {
    await browser?.close();
  }
}
