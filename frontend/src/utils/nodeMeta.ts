import type { Importance, NodeType } from "@/types";
import {
  Lightbulb, StickyNote, BookOpen, HelpCircle, Link2, FolderKanban,
  Book, GraduationCap, User, Hash, FileText,
} from "lucide-react";

export const NODE_TYPE_META: Record<NodeType, { label: string; color: string; icon: any }> = {
  IDEA: { label: "Idea", color: "#F5B95C", icon: Lightbulb },
  NOTE: { label: "Note", color: "#7C8CFF", icon: StickyNote },
  CONCEPT: { label: "Concept", color: "#5CD6C0", icon: BookOpen },
  QUESTION: { label: "Question", color: "#F27878", icon: HelpCircle },
  RESOURCE: { label: "Resource", color: "#B98CE8", icon: Link2 },
  PROJECT: { label: "Project", color: "#5CC2F2", icon: FolderKanban },
  BOOK: { label: "Book", color: "#E89A5C", icon: Book },
  COURSE: { label: "Course", color: "#8CD65C", icon: GraduationCap },
  PERSON: { label: "Person", color: "#F28CC5", icon: User },
  TOPIC: { label: "Topic", color: "#5C9DE8", icon: Hash },
  REFERENCE: { label: "Reference", color: "#A0A8B8", icon: FileText },
};

export const IMPORTANCE_META: Record<Importance, { label: string; weight: number }> = {
  LOW: { label: "Low", weight: 1 },
  MEDIUM: { label: "Medium", weight: 2 },
  HIGH: { label: "High", weight: 3 },
  CRITICAL: { label: "Critical", weight: 4 },
};
