import { AppChrome } from "@/components/layout/AppChrome";
import { PhotoGrid } from "@/components/photos/PhotoGrid";

export default function HomePage() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <AppChrome />
      <main className="flex flex-1 flex-col overflow-hidden">
        <PhotoGrid />
      </main>
    </div>
  );
}
