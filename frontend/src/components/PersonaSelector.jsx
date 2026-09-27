import React from 'react';
import { User, Briefcase, FileCheck, Info } from 'lucide-react';

export const PERSONAS = [
  {
    id: 'consumer',
    name: 'Consumer',
    icon: User,
    color: 'emerald',
    badgeClass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    description: 'Simple explanations with minimal jargon in plain English.',
  },
  {
    id: 'professional',
    name: 'Professional',
    icon: FileCheck,
    color: 'indigo',
    badgeClass: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
    description: 'Technical explanations with precise terms, clauses, and section references.',
  },
  {
    id: 'business',
    name: 'Business',
    icon: Briefcase,
    color: 'amber',
    badgeClass: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    description: 'Focus on costs, obligations, deadlines, liabilities, and operational impact.',
  },
];

export default function PersonaSelector({ selectedPersona, onChange, size = 'md' }) {
  const currentPersona = PERSONAS.find((p) => p.id === selectedPersona) || PERSONAS[0];

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
          <span>Explanation Style Persona:</span>
          <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold border ${currentPersona.badgeClass}`}>
            {currentPersona.name} Mode
          </span>
        </label>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {PERSONAS.map((p) => {
          const Icon = p.icon;
          const isSelected = selectedPersona === p.id;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onChange(p.id)}
              className={`p-3 rounded-xl border text-left transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-slate-800/90 border-purple-500 shadow-md shadow-purple-500/10 ring-1 ring-purple-500'
                  : 'bg-slate-950/60 border-slate-800 hover:border-slate-700/80 hover:bg-slate-900/60'
              }`}
            >
              <div className="flex items-center gap-2">
                <div
                  className={`p-1.5 rounded-lg shrink-0 ${
                    isSelected ? 'bg-purple-500/20 text-purple-300' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <span className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                  {p.name}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5 leading-snug line-clamp-2">
                {p.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
