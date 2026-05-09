import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register } from '../api/auth';

const styles = {
  container: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  card: { background: '#fff', padding: '2rem', borderRadius: '8px', boxShadow: '0 2px 12px rgba(0,0,0,0.1)', width: '100%', maxWidth: '360px' },
  title: { marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: 600, textAlign: 'center' },
  field: { marginBottom: '1rem' },
  label: { display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', color: '#555' },
  input: { width: '100%', padding: '0.6rem 0.75rem', border: '1px solid #ddd', borderRadius: '4px', fontSize: '1rem' },
  btn: { width: '100%', padding: '0.7rem', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '1rem', cursor: 'pointer', marginTop: '0.5rem' },
  error: { color: '#dc2626', marginBottom: '1rem', fontSize: '0.875rem' },
  link: { display: 'block', textAlign: 'center', marginTop: '1rem', color: '#4f46e5', textDecoration: 'none' },
};

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Регистрация</h1>
        <form onSubmit={handleSubmit}>
          {error && <div style={styles.error}>{error}</div>}
          {['email', 'username', 'password'].map((field) => (
            <div key={field} style={styles.field}>
              <label style={styles.label}>{field === 'email' ? 'Email' : field === 'username' ? 'Имя пользователя' : 'Пароль'}</label>
              <input style={styles.input} name={field} type={field === 'password' ? 'password' : 'text'} value={form[field]} onChange={handleChange} required />
            </div>
          ))}
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>
        <Link style={styles.link} to="/login">Уже есть аккаунт? Войти</Link>
      </div>
    </div>
  );
}
