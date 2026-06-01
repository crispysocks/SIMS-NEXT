import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '../error-boundary';

function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('boom');
  return <div>safe</div>;
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary level="page">
        <Bomb shouldThrow={false} />
      </ErrorBoundary>
    );
    expect(screen.getByText('safe')).toBeInTheDocument();
  });

  it('catches error and shows page-level fallback', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <ErrorBoundary level="page">
        <Bomb shouldThrow />
      </ErrorBoundary>
    );
    expect(screen.getByText(/页面出错了/i)).toBeInTheDocument();
    spy.mockRestore();
  });

  it('catches error and shows section-level fallback', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <ErrorBoundary level="section">
        <Bomb shouldThrow />
      </ErrorBoundary>
    );
    expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
    spy.mockRestore();
  });

  it('catches error and shows app-level fallback', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <ErrorBoundary level="app">
        <Bomb shouldThrow />
      </ErrorBoundary>
    );
    expect(screen.getByText(/应用出错/i)).toBeInTheDocument();
    spy.mockRestore();
  });

  it('calls onError when error is caught', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const onError = vi.fn();
    render(
      <ErrorBoundary level="section" onError={onError}>
        <Bomb shouldThrow />
      </ErrorBoundary>
    );
    expect(onError).toHaveBeenCalled();
    spy.mockRestore();
  });
});
