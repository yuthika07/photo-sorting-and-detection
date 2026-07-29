import { PersonShelf } from "@/components/people/PersonShelf";
import { SearchBar } from "@/components/search/SearchBar";
import { TitleBar } from "@/components/layout/TitleBar";

/**
 * Everything above the paper content area lives on one continuous
 * dark "chrome" surface — title bar, search well, and the people
 * shelf's recessed rail — so it reads as a single physical panel of
 * brushed metal rather than several stacked bars.
 */
export function AppChrome() {
  return (
    <header className="chrome-surface relative z-10 border-b border-black/50">
      <TitleBar />
      <div className="border-t border-white/[0.04]">
        <SearchBar />
      </div>
      <div className="border-t border-white/[0.04] pt-2">
        <PersonShelf />
      </div>
    </header>
  );
}
