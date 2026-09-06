import { useCallback, useEffect, useRef, useState } from "react";

const EMPTY_DEPS: unknown[] = [];

export function useApi<T>(loader: () => Promise<T>, deps: unknown[] = EMPTY_DEPS) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  const reload = useCallback((opts?: { silent?: boolean }) => {
    let cancelled = false;
    if (!opts?.silent) setLoading(true);
    setError(null);
    loaderRef.current()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, deps);

  useEffect(() => reload(), [reload]);

  return { data, error, loading, reload };
}
