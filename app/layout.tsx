import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mines Signal System",
  description:
    "Mines signal management and Telegram publishing platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}