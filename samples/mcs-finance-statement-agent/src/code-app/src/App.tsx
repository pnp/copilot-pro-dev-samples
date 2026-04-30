import { SonnerProvider } from "@/providers/sonner-provider"
import { QueryProvider } from "./providers/query-provider"
import { RouterProvider } from "react-router-dom"
import { router } from "@/router"

export default function App() {
  return (
    <SonnerProvider>
      <QueryProvider>
        <RouterProvider router={router} />
      </QueryProvider>
    </SonnerProvider>
  )
}
