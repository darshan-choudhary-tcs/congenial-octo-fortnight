
import * as React from "react"



import { cn } from "@/lib/utils"



export interface TextareaProps

  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}



const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(

  ({ className, ...props }, ref) => {

    return (

      <textarea

        className={cn(

          "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-The problem is that the Textarea component file doesn't exist in your components directory. You need to create the textarea component file with a custom implementation.



```bash

mkdir -p components/ui && cat > components/ui/textarea.tsx << 'EOF'

import * as React from "react"



export interface TextareaProps

  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}



const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(

  ({ className = "", ...props }, ref) => {

    const baseClasses = "flex min-h-[80px] w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50"

    

    return (

      <textarea

        className={`${baseClasses} ${className}`}

        ref={ref}

        {...props}

      />

    )

  }

)



Textarea.displayName = "Textarea"



export { Textarea }

