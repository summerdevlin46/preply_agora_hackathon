import type { Metadata } from "next";
import "./globals.css";
import StyledComponentsRegistry from "./StyledComponentsRegistry";
import PreplyTopBar from "./PreplyTopBar";

export const metadata: Metadata = {
  title: "Mirror Frontend",
  description: "Next frontend for the Mirror worksheet parsing and exercise API",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
    <head>
        <title>Preply</title>
        <link
          rel="preload"
          href="https://preply.com/fonts/Platform-Medium-Web-v0.woff2"
          as="font"
          type="font/woff2"
          crossOrigin=""
        />
        <link
          rel="preload"
          href="https://static.preply.com/ds/fonts/en/PreplyInter.regular.woff2"
          as="font"
          type="font/woff2"
          crossOrigin=""
        />
    </head>
    <body className="flex min-h-full flex-col">
    <StyledComponentsRegistry>
      <PreplyTopBar />
      {children}
    </StyledComponentsRegistry>
    </body>
    </html>
  );
}
