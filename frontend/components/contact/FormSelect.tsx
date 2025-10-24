import {memo, ChangeEvent} from 'react'

interface FormSelectProps {
  id: string
  name: string
  label: string
  required?: boolean
  value: string
  onChange: (e: ChangeEvent<HTMLSelectElement>) => void
  options: {value: string; label: string}[]
  placeholder: string
}

export const FormSelect = memo(({
  id,
  name,
  label,
  required = false,
  value,
  onChange,
  options,
  placeholder
}: FormSelectProps) => {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium mb-2">
        {label} {required && '*'}
      </label>
      <select
        id={id}
        name={name}
        required={required}
        value={value}
        onChange={onChange}
        className="w-full px-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
})

FormSelect.displayName = 'FormSelect'
