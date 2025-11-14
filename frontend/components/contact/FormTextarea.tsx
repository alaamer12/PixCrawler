import {memo, ChangeEvent} from 'react'

interface FormTextareaProps {
  id: string
  name: string
  label: string
  required?: boolean
  value: string
  onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void
  placeholder: string
  rows?: number
}

export const FormTextarea = memo(({
                                    id,
                                    name,
                                    label,
                                    required = false,
                                    value,
                                    onChange,
                                    placeholder,
                                    rows = 6
                                  }: FormTextareaProps) => {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium mb-2">
        {label} {required && '*'}
      </label>
      <textarea
        id={id}
        name={name}
        required={required}
        rows={rows}
        value={value}
        onChange={onChange}
        className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
        placeholder={placeholder}
      />
    </div>
  )
})

FormTextarea.displayName = 'FormTextarea'
