import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "@/stores/user";

import Conversation from "@/components/Conversation.vue";
import HomeView from "@/components/HomeView.vue";
import LoginView from "@/components/LoginView.vue";
import RegisterView from "@/components/RegisterView.vue";
import ParentRegister from "@/components/ParentRegister.vue";
import JoinUs from "@/components/JoinUs.vue";
import ParentDashboard from "@/components/ParentDashboard.vue";
import StudentDashboard from "@/components/StudentDashboard.vue";
import Lifeskills from "@/components/LifeSkills.vue";
import SafetySkills from "@/components/SafetySkills.vue";
import FinanceSkills from "@/components/FinancialLiteracy.vue";
import FinanceGame from "@/components/FinanceGame.vue";
import SafetyVideo from "@/components/SafetyVideo.vue";
import SafetyComic from "@/components/SafetyComic.vue";
import SafetyvidView from "@/components/SafetyvidView.vue";
import SafetycomView from "@/components/SafetycomView.vue";
import SafetycomQuiz from "@/components/SafetycomQuiz.vue";
import SafetyvidQuiz from "@/components/SafetyvidQuiz.vue";
import FinanceVideo from "@/components/FinanceVideo.vue";
import FinancevidQuiz from "@/components/FinancevidQuiz.vue";
import FinancevidView from "@/components/FinancevidView.vue";
import AdminSkill from "@/components/AdminSkill.vue";
import AdminDashboard from '@/components/AdminDashboard.vue'
import AdminSafety from '@/components/AdminSafety.vue'
import AdminFinance from '@/components/AdminFinance.vue'
import ProblemSolving from '@/components/ProblemSolving.vue'
import ChatBot from "@/components/ChatBot.vue";
import DairyEntry from "@/components/DairyEntry.vue";
import Profile from "@/components/Profile.vue";
import AdminBadge from "@/components/AdminBadge.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/login",
    name: "login",
    component: LoginView,
  },
  {
    path: "/join-us",
    name: "join-us",
    component: JoinUs,
  },
  {
    path: "/register-parent",
    name: "parent-register",
    component: ParentRegister,
  },
  {
    path: "/register",
    name: "register",
    component: RegisterView,
  },
  {
    path: "/student-dashboard",
    name: "student-dashboard",
    component: StudentDashboard,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/conversation",
    name: "conversation",
    component: Conversation,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/parent-dashboard",
    name: "parent-dashboard",
    component: ParentDashboard,
    meta: { requiresAuth: true, role: 'parent' },
  },
  {
    path: "/lifeskills",
    name: "lifeskills",
    component: Lifeskills,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/safetyskills",
    name: "safetyskills",
    component: SafetySkills,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/financeskills",
    name: "financeskills",
    component: FinanceSkills,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/financegame",
    name: "financegame",
    component: FinanceGame,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/safetyvideo",
    name: "safetyvideo",
    component: SafetyVideo,
    props: (route) => ({ init: route.params.id }),
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/safetycomic",
    name: "safetycomic",
    component: SafetyComic,
    props: (route) => ({ init: route.params.id }),
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/safetycomic/:id",
    name: "safety-comic-view",
    component: SafetycomView,
    props: (route) => ({ init: route.params.id }),
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/safetyvideo/:id",
    name: "safety-video-view",
    component: SafetyvidView,
    props: (route) => ({ init: route.params.id }),
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/safetycomicquiz/:id",
    name: "safetycomicquiz",
    component: SafetycomQuiz,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/safetyvideoquiz/:id",
    name: "safetyvideoquiz",
    component: SafetyvidQuiz,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/financevideo",
    name: "financevideo",
    component: FinanceVideo,
    props: (route) => ({ init: route.params.id }),
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/financevideo/:id",
    name: "finance-video-view",
    component: FinancevidView,
    props: (route) => ({ init: route.params.id }),
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: "/financevideoquiz/:id",
    name: "financevideoquiz",
    component: FinancevidQuiz,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: '/problem-solving',
    name: 'problem-solving',
    component: ProblemSolving,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: '/chatbox',
    name: 'chatbox',
    component: ChatBot,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: '/dairy',
    name: 'dairy',   
    component: DairyEntry,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: Profile,
    meta: { requiresAuth: true, role: 'user' },
  },
  {
    path: '/admin-skill',
    name: 'admin-skill',
    component: AdminSkill,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/admin-badge',
    name: 'admin-badge',
    component: AdminBadge,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: "/admin-safety",
    name: "admin-safety",
    component: AdminSafety,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: "/admin-finance",
    name: "admin-finance",
    component: AdminFinance,
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: "/admin-dashboard",
    name: "admin-dashboard",
    component: AdminDashboard,
    meta: { requiresAuth: true, role: 'admin' },
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Role-based guard
router.beforeEach((to, from, next) => {
  const userStore = useUserStore();
  userStore.loadUser(); // restore from localStorage

  if (to.meta.requiresAuth) {
    if (!userStore.token) {
      alert("🔐 Please log in first.");
      return next("/login");
    }

    if (to.meta.role && userStore.role !== to.meta.role) {
      alert("⛔ Access denied.");
      return next("/");
    }
  }

  next();
});

export default router;
export { router };