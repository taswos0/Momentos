export const metadata = {
  title: "Momentos",
  description: "Transmedia Alchemist control panel"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "Segoe UI, sans-serif", background: "#f5f7fb" }}>
        {children}
      </body>
    </html>
  );
}
