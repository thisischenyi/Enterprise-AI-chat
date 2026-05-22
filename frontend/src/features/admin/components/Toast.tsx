import { useEffect, useState } from "react";

interface ToastProps {
  message: string;
  onClose: () => void;
}

export default function Toast({ message, onClose }: ToastProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      onClose();
    }, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  if (!visible) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-green-600 text-white rounded-lg px-4 py-2 shadow-lg z-50">
      {message}
    </div>
  );
}
