import { useFetch } from "@/hooks/useFetch";
import type { User } from "@/types";
import SectionCard from "@/components/SectionCard";
import styles from "./Profile.module.css";

export default function Profile() {
  const { data, loading, error } = useFetch<User>("/users/me");

  if (loading) return <p className={styles.state}>Loading profile...</p>;
  if (error) return <p className={styles.error}>{error}</p>;
  if (!data) return <p className={styles.state}>Not signed in.</p>;

  return (
    <main className={styles.main}>
      <SectionCard title="My Profile">
        <div className={styles.avatar}>
          {data.avatar_url ? (
            <img src={data.avatar_url} alt={data.full_name} />
          ) : (
            <div className={styles.avatarPlaceholder}>
              {data.full_name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        <h2 className={styles.name}>{data.full_name}</h2>
        <p className={styles.email}>{data.email}</p>
        <span className={`${styles.role} ${styles[data.role]}`}>
          {data.role}
        </span>
      </SectionCard>
    </main>
  );
}
