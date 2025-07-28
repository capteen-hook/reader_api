"use client";
import React from "react";

export default function ToolSwitch({ onToggle }: { onToggle: (state: boolean) => void }) {
  const [switchState, setSwitchState] = React.useState(false);

    const handleToggle = () => {
        setSwitchState(!switchState);
        onToggle(!switchState);
    };

    return (
        <button className="m-2 p-2 bg-gray-200 rounded" onClick={handleToggle}>
            {switchState ? "Disable Tools" : "Enable Tools"}
        </button>
    );      
}