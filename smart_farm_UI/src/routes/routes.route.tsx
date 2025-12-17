import Auth from "@/screen/auth";
import History from "@/screen/history";
import Main from "@/screen/main";

export const routes = [
  { path: "/", element: <Main /> },
  { path: "/history", element: <History /> },
  { path: "/auth", element: <Auth /> },
];
