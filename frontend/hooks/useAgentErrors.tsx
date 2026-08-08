import { ReactNode, useEffect } from 'react';
import { toast as sonnerToast } from 'sonner';
import { useAgent, useSessionContext } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ToastProps {
  title: ReactNode;
  description: ReactNode;
}

function toastAlert(toast: ToastProps) {
  const { title, description } = toast;

  return sonnerToast.custom(
    (id) => (
      <Alert onClick={() => sonnerToast.dismiss(id)} className="bg-accent w-full md:w-[364px]">
        <WarningIcon weight="bold" />
        <AlertTitle>{title}</AlertTitle>
        {description && <AlertDescription>{description}</AlertDescription>}
      </Alert>
    ),
    { duration: 12_000 }
  );
}

export function useAgentErrors() {
  const agent = useAgent();
  const { isConnected, end } = useSessionContext();

  useEffect(() => {
    if (isConnected && agent.state === 'failed') {
      const reasons = agent.failureReasons || [];

      // Check if it looks like a microphone permission problem
      const isMicError = reasons.some(
        (r) =>
          r.toLowerCase().includes('permissiondenied') ||
          r.toLowerCase().includes('notallowederror') ||
          r.toLowerCase().includes('microphone')
      );

      if (isMicError) {
        toastAlert({
          title: 'Microphone access blocked',
          description: (
            <div className="space-y-2">
              <p>Please allow microphone permission to talk to Kisan Sakhi.</p>
              <p className="text-sm opacity-80">
                Click the lock icon in the address bar → Site settings → Allow Microphone → then try again.
              </p>
            </div>
          ),
        });
      } else {
        toastAlert({
          title: 'Session ended',
          description: (
            <div className="space-y-2">
              {reasons.length > 0 && <p>{reasons[0]}</p>}
              <p>Please try starting the conversation again.</p>
            </div>
          ),
        });
      }

      end();
    }
  }, [agent, isConnected, end]);
}