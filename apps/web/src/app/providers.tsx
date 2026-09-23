"use client";

import React, { useState } from "react";
import { useServerInsertedHTML } from "next/navigation";
import {
  createDOMRenderer,
  RendererProvider,
  FluentProvider,
  webLightTheme,
  renderToStyleElements,
  SSRProvider,
} from "@fluentui/react-components";

export function Providers({ children }: { children: React.ReactNode }) {
  const [renderer] = useState(() => createDOMRenderer());

  useServerInsertedHTML(() => {
    return <>{renderToStyleElements(renderer)}</>;
  });

  return (
    <RendererProvider renderer={renderer}>
      <SSRProvider>
        <FluentProvider theme={webLightTheme}>
          {children}
        </FluentProvider>
      </SSRProvider>
    </RendererProvider>
  );
}
