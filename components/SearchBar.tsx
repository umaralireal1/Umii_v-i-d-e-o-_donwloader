import React, { useState } from 'react';
import { Search, Link as LinkIcon, X, Sparkles } from 'lucide-react';

interface SearchBarProps {
  onSearch: (url: string) => void;
  isLoading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [url, setUrl] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSearch(url.trim());
    }
  };

  const clearInput = () => setUrl('');

  return (
    <div className="w-full max-w-2xl perspective-1000 z-20">
      <form 
        onSubmit={handleSubmit} 
        className={`
          relative group transition-all duration-500 transform
          ${isFocused ? 'scale-105 rotate-x-2' : 'hover:scale-[1.02]'}
        `}
      >
        {/* Animated Glow Background */}
        <div className="absolute -inset-1 bg-gradient-to-r from-pink-600 via-purple-600 to-cyan-600 rounded-2xl blur opacity-40 group-hover:opacity-100 animate-gradient-xy transition duration-1000"></div>
        
        {/* Glass Container */}
        <div className="relative flex items-center bg-black/60 backdrop-blur-xl border border-white/10 rounded-2xl p-2 shadow-2xl overflow-hidden">
          
          <div className="pl-4 pr-3 text-fuchsia-400 animate-pulse">
            <LinkIcon size={22} />
          </div>
          
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Paste TikTok, YouTube, or Instagram link..."
            className="flex-1 bg-transparent text-white placeholder-slate-400 outline-none h-14 px-2 font-medium text-lg"
            disabled={isLoading}
          />

          {url && (
            <button
              type="button"
              onClick={clearInput}
              className="p-2 text-slate-400 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
          )}

          <button
            type="submit"
            disabled={isLoading || !url}
            className={`
              ml-2 px-8 h-12 rounded-xl font-bold flex items-center gap-2 transition-all duration-300 transform
              ${isLoading || !url 
                ? 'bg-slate-800/50 text-slate-500 cursor-not-allowed' 
                : 'bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 text-white shadow-[0_0_20px_rgba(192,38,211,0.5)] hover:shadow-[0_0_30px_rgba(192,38,211,0.7)] hover:-translate-y-0.5'
              }
            `}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Loading</span>
              </span>
            ) : (
              <>
                <Sparkles size={18} className={url ? "animate-spin-slow" : ""} />
                <span>Fetch</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SearchBar;