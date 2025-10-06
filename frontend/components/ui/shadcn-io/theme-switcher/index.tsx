'use client';

import {useControllableState} from '@radix-ui/react-use-controllable-state';
import {Check, ChevronDown, Monitor, Moon, Sun} from 'lucide-react';
import {useCallback, useEffect, useRef, useState} from 'react';
import {cn} from '@/lib/utils';

const themes = [
  {
    key: 'system',
    icon: Monitor,
    label: 'System',
  },
  {
    key: 'light',
    icon: Sun,
    label: 'Light',
  },
  {
    key: 'dark',
    icon: Moon,
    label: 'Dark',
  },
];

export type ThemeSwitcherProps = {
  value?: 'light' | 'dark' | 'system';
  onChange?: (theme: 'light' | 'dark' | 'system') => void;
  defaultValue?: 'light' | 'dark' | 'system';
  className?: string;
};

export const ThemeSwitcher = ({
                                value,
                                onChange,
                                defaultValue = 'system',
                                className,
                              }: ThemeSwitcherProps) => {
  const [theme, setTheme] = useControllableState({
    defaultProp: defaultValue,
    prop: value,
    onChange,
  });
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleThemeClick = useCallback(
    (themeKey: 'light' | 'dark' | 'system') => {
      setTheme(themeKey);
      setIsOpen(false);
    },
    [setTheme]
  );

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  if (!mounted) {
    return null;
  }

  const currentTheme = themes.find(t => t.key === theme);
  const CurrentIcon = currentTheme?.icon || Monitor;

  return (
    <div className={cn('relative', className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-muted/80 hover:border-primary/30 transition-all cursor-pointer active:scale-95"
        aria-label="Select theme"
        type="button"
      >
        <CurrentIcon className="h-4 w-4 transition-colors group-hover:text-primary"/>
        {/* <span className="text-sm">{currentTheme?.label}</span> */}
        <ChevronDown className={cn('h-3 w-3 transition-transform', isOpen && 'rotate-180')}/>
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-40 bg-card border border-border rounded-lg shadow-lg overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          {themes.map(({key, icon: Icon, label}) => {
            const isActive = theme === key;

            return (
              <button
                key={key}
                onClick={() => handleThemeClick(key as 'light' | 'dark' | 'system')}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors cursor-pointer',
                  isActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'hover:bg-muted text-foreground'
                )}
                type="button"
              >
                <Icon className="h-4 w-4"/>
                <span className="flex-1 text-left">{label}</span>
                {isActive && <Check className="h-4 w-4"/>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
