export default function debounce<T extends (...args: any[]) => void>(
  fn: T,
  wait: number,
) {
  let timeoutId: ReturnType<typeof setTimeout> | undefined;

  return function debounced(this: ThisParameterType<T>, ...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn.apply(this, args);
    }, wait);
  };
}
