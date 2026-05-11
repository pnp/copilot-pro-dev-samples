import { createBrowserRouter } from "react-router-dom";
import Layout from "@/pages/_layout";
import ReviewPage from "@/pages/review";
import NotFoundPage from "@/pages/not-found";

// IMPORTANT: Do not remove or modify the code below!
// Normalize basename when hosted in Power Apps
const BASENAME = new URL(".", location.href).pathname;
if (location.pathname.endsWith("/index.html")) {
  history.replaceState(null, "", BASENAME + location.search + location.hash);
}

export const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <Layout />,
      errorElement: <NotFoundPage />,
      children: [
        { index: true, element: <ReviewPage /> },
      ],
    },
  ],
  {
    basename: BASENAME,
  }
);
