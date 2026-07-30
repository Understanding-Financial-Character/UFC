import { Provider } from "react-redux";
import { RouterProvider } from "react-router-dom";

import { router } from "../router/router";
import { store } from "../store";

export function AppProviders() {
  return (
    <Provider store={store}>
      <RouterProvider router={router} />
    </Provider>
  );
}
