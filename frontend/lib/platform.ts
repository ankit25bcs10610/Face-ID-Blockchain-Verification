import { Facebook, Github, Globe, Instagram, Linkedin, MessageCircle, Twitter, Youtube } from "lucide-react";

const PATTERNS: Array<{ test: RegExp; icon: typeof Globe; label: string }> = [
  { test: /instagram\.com$/, icon: Instagram, label: "Instagram" },
  { test: /(twitter\.com|x\.com)$/, icon: Twitter, label: "X" },
  { test: /linkedin\.com$/, icon: Linkedin, label: "LinkedIn" },
  { test: /facebook\.com$/, icon: Facebook, label: "Facebook" },
  { test: /reddit\.com$/, icon: MessageCircle, label: "Reddit" },
  { test: /(youtube\.com|youtu\.be)$/, icon: Youtube, label: "YouTube" },
  { test: /github\.com$/, icon: Github, label: "GitHub" }
];

export function hostnameOf(url?: string): string {
  if (!url) return "";
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export function platformFor(url?: string) {
  const host = hostnameOf(url);
  const match = PATTERNS.find((entry) => entry.test.test(host));
  if (match) return { Icon: match.icon, label: match.label };
  return { Icon: Globe, label: host || "Web" };
}
