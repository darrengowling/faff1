import { useTheme } from "next-themes"
import { Toaster as Sonner } from "sonner"
import { TESTIDS } from "../../testids"

const Toaster = ({
  ...props
}) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-muted-foreground",
          actionButton:
            "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton:
            "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
          error: `group toast ${TESTIDS.errorToast}`,
          success: `group toast ${TESTIDS.successToast}`,
          info: `group toast ${TESTIDS.infoToast}`,
        },
        unstyled: false,
        duration: 4000,
      }}
      {...props} />
  );
}

export { Toaster }
