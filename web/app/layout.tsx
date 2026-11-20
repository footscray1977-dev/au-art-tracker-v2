export const metadata = {
  title: "Michael's Art Tracker — Overseas Sleeper Digest",
  description: "Australian art sleeper-lot hunter: 946 artists, 339 overseas auction houses, ranked daily at 3am Brisbane.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, background: '#F7F5F0' }}>{children}</body>
    </html>
  );
}
