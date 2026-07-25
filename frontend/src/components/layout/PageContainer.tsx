import type { PropsWithChildren } from 'react';

interface PageContainerProps extends PropsWithChildren {
  className?: string;
}

export function PageContainer({ className = '', children }: PageContainerProps) {
  return <main className={`page ${className}`.trim()}>{children}</main>;
}
