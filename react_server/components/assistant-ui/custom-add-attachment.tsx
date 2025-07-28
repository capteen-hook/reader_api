"use client";
import {
  ComponentRef,
  forwardRef,
  ComponentPropsWithoutRef,
  MouseEventHandler,
} from "react";
import { Primitive } from "@radix-ui/react-primitive";
import { composeEventHandlers } from "@radix-ui/primitive";
import { useCallback } from "react";
import { useComposer, useComposerRuntime } from "@assistant-ui/react";

import { makeSpecial } from "@/components/special_file"

const useComposerAddAttachment = ({
  multiple = true,
  processType,
}: {
  /** allow selecting multiple files */
  multiple?: boolean | undefined;
  /** how to handle the attachment */
  processType?: "file" | "report" | "appliance";
} = {}) => {
  if (!processType) {
    console.warn('processType is not set, defaulting to "file"');
    processType = "file";
  }

  const disabled = useComposer((c) => !c.isEditing);

  const composerRuntime = useComposerRuntime();
  const callback = useCallback(() => {
    const input = document.createElement("input");
    input.type = "file";
    input.multiple = multiple;
    input.hidden = true;

    const attachmentAccept = composerRuntime.getAttachmentAccept();
    if (attachmentAccept !== "*") {
      input.accept = attachmentAccept;
    }

    document.body.appendChild(input);

    input.onchange = (e) => {
      const fileList = (e.target as HTMLInputElement).files;
      if (!fileList) return;
      for (const file of fileList) {
        const specialFile = makeSpecial(file, processType);
        composerRuntime.addAttachment(specialFile);
      }

      document.body.removeChild(input);
    };

    input.oncancel = () => {
      if (!input.files || input.files.length === 0) {
        document.body.removeChild(input);
      }
    };

    input.click();
  }, [composerRuntime, multiple, processType]);

  if (disabled) return null;
  return callback;
};

export type Element = ActionButtonElement;
export type Props = ActionButtonProps<typeof useComposerAddAttachment>;

type ActionButtonCallback<TProps> = (
  props: TProps,
) => MouseEventHandler<HTMLButtonElement> | null;

type PrimitiveButtonProps = ComponentPropsWithoutRef<typeof Primitive.button>;

export type ActionButtonProps<THook> = PrimitiveButtonProps &
  (THook extends (props: infer TProps) => unknown ? TProps : never);

export type ActionButtonElement = ComponentRef<typeof Primitive.button>;

export const createActionButton = <TProps,>(
  displayName: string,
  useActionButton: ActionButtonCallback<TProps>,
  forwardProps: (keyof NonNullable<TProps>)[] = [],
) => {
  const ActionButton = forwardRef<
    ActionButtonElement,
    PrimitiveButtonProps & TProps
  >((props, forwardedRef) => {
    const forwardedProps = {} as TProps;
    const primitiveProps = {} as PrimitiveButtonProps;
    
    (Object.keys(props) as Array<keyof typeof props>).forEach((key) => {
      if (forwardProps.includes(key as keyof TProps)) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (forwardedProps as any)[key] = props[key];
      } else if (key !== "processType") { // Exclude processType from DOM props
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (primitiveProps as any)[key] = props[key];
      }
    });


    const callback = useActionButton(forwardedProps as TProps) ?? undefined;
    return (
      <Primitive.button
        type="button"
        {...primitiveProps}
        ref={forwardedRef}
        disabled={primitiveProps.disabled || !callback}
        onClick={composeEventHandlers(primitiveProps.onClick, callback)}
      />
    );
  });

  ActionButton.displayName = displayName;

  return ActionButton;
};

export const CustomAddAttachment = createActionButton(
  "ComposerPrimitive.AddAttachment",
  useComposerAddAttachment,
  ["multiple", "processType"] // Forward these props to the hook
);
