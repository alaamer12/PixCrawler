import {memo, ChangeEvent} from 'react'

interface FormFieldProps {
  id: string
  name: string
  label: string
  type?: 'text' | 'email'
  required?: boolean
  value: string
  onChange: (e: ChangeEvent<HTMLInputElement>) => void
  placeholder: string
}

export const FormField = memo(({
  id,
  name,
  label,
  type = 'text',
  required = false,
  value,
  onChange,
  placeholder
}: FormFieldProps) => {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium mb-2">
        {label} {required && '*'}
      </label>
      <input
        type={type}
        id={id}
        name={name}
        required={required}
        value={value}
        onChange={onChange}
        className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
        placeholder={placeholder}
      />
    </div>
  )
})

FormField.displayName = 'FormField'
