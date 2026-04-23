import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import './App.css'

type Expense = {
  id: string
  amount: string
  category: string
  description: string
  date: string
  created_at: string
}

type ExpenseFormData = {
  amount: string
  category: string
  description: string
  date: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const CATEGORIES = [
  'food',
  'transport',
  'utilities',
  'entertainment',
  'shopping',
  'healthcare',
  'other',
]

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(value)
}

const createIdempotencyKey = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function App() {
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [categoryFilter, setCategoryFilter] = useState('')
  const [sortOrder, setSortOrder] = useState('date_desc')
  const [isFetching, setIsFetching] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [fetchError, setFetchError] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [pendingIdempotencyKey, setPendingIdempotencyKey] = useState('')
  const [backendStatus, setBackendStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking')
  const [formData, setFormData] = useState<ExpenseFormData>({
    amount: '',
    category: 'food',
    description: '',
    date: '',
  })

  const totalVisibleExpenses = useMemo(() => {
    return expenses.reduce((sum, expense) => sum + Number(expense.amount), 0)
  }, [expenses])

  useEffect(() => {
    const controller = new AbortController()

    const loadExpenses = async () => {
      setIsFetching(true)
      setFetchError('')

      try {
        const params = new URLSearchParams()
        if (categoryFilter) {
          params.set('category', categoryFilter)
        }
        if (sortOrder) {
          params.set('sort', sortOrder)
        }

        const response = await fetch(
          `${API_BASE_URL}/expenses?${params.toString()}`,
          { signal: controller.signal },
        )

        if (!response.ok) {
          throw new Error('Unable to fetch expenses right now.')
        }

        const data: Expense[] = await response.json()
        setExpenses(data)
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }

        setFetchError(
          error instanceof Error
            ? error.message
            : 'Something went wrong while loading expenses.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsFetching(false)
        }
      }
    }

    loadExpenses()

    return () => {
      controller.abort()
    }
  }, [categoryFilter, sortOrder])

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`)
        if (response.ok) {
          setBackendStatus('healthy')
        } else {
          setBackendStatus('unhealthy')
        }
      } catch {
        setBackendStatus('unhealthy')
      }
    }

    checkHealth()
    const healthCheckInterval = setInterval(checkHealth, 30000)

    return () => {
      clearInterval(healthCheckInterval)
    }
  }, [])

  const handleInputChange = (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = event.target
    setFormData((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    setSubmitError('')
    setIsSubmitting(true)

    const idempotencyKey = pendingIdempotencyKey || createIdempotencyKey()
    if (!pendingIdempotencyKey) {
      setPendingIdempotencyKey(idempotencyKey)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/expenses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify({
          amount: formData.amount,
          category: formData.category,
          description: formData.description,
          date: formData.date,
        }),
      })

      if (!response.ok) {
        const errorPayload = await response.json().catch(() => null)
        if (errorPayload && typeof errorPayload === 'object') {
          const firstError = Object.values(errorPayload)[0]
          if (Array.isArray(firstError) && firstError.length > 0) {
            throw new Error(String(firstError[0]))
          }
        }

        throw new Error('Unable to save expense. Please try again.')
      }

      setPendingIdempotencyKey('')
      setFormData({ amount: '', category: 'food', description: '', date: '' })

      const params = new URLSearchParams()
      if (categoryFilter) {
        params.set('category', categoryFilter)
      }
      if (sortOrder) {
        params.set('sort', sortOrder)
      }

      const listResponse = await fetch(`${API_BASE_URL}/expenses?${params.toString()}`)
      if (!listResponse.ok) {
        throw new Error('Expense saved, but list refresh failed. Please reload.')
      }

      const listData: Expense[] = await listResponse.json()
      setExpenses(listData)
    } catch (error) {
      setSubmitError(
        error instanceof Error
          ? error.message
          : 'Something went wrong while saving the expense.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="header">
        <div className="header-top">
          <div>
            <h1>Expense Tracker</h1>
            <p>Track spending with retry-safe expense creation.</p>
          </div>
          <div className={`status-badge status-${backendStatus}`}>
            <span className="status-dot"></span>
            {backendStatus === 'healthy' && 'Backend Online'}
            {backendStatus === 'unhealthy' && 'Backend Offline'}
            {backendStatus === 'checking' && 'Checking...'}
          </div>
        </div>
      </header>

      <section className="card">
        <h2>Add Expense</h2>
        <form className="expense-form" onSubmit={handleSubmit}>
          <label>
            Amount
            <input
              type="number"
              step="0.01"
              min="0.01"
              name="amount"
              value={formData.amount}
              onChange={handleInputChange}
              required
            />
          </label>

          <label>
            Category
            <select name="category" value={formData.category} onChange={handleInputChange}>
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label>
            Description
            <input
              type="text"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              maxLength={500}
              placeholder="Optional note"
            />
          </label>

          <label>
            Date
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleInputChange}
              required
            />
          </label>

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Add Expense'}
          </button>
        </form>
        {submitError && <p className="error">{submitError}</p>}
      </section>

      <section className="card">
        <div className="toolbar">
          <h2>Expenses</h2>
          <div className="controls">
            <label>
              Filter
              <select
                value={categoryFilter}
                onChange={(event) => setCategoryFilter(event.target.value)}
              >
                <option value="">All categories</option>
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Sort
              <select
                value={sortOrder}
                onChange={(event) => setSortOrder(event.target.value)}
              >
                <option value="date_desc">Newest first</option>
                <option value="date_asc">Oldest first</option>
              </select>
            </label>
          </div>
        </div>

        <p className="total">Total: {formatCurrency(totalVisibleExpenses)}</p>

        {fetchError && <p className="error">{fetchError}</p>}

        {isFetching ? (
          <p>Loading expenses...</p>
        ) : expenses.length === 0 ? (
          <p>No expenses found for current filters.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th className="amount">Amount</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <tr key={expense.id}>
                    <td>{expense.date}</td>
                    <td className="capitalize">{expense.category}</td>
                    <td>{expense.description || '-'}</td>
                    <td className="amount">{formatCurrency(Number(expense.amount))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  )
}

export default App
