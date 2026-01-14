import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

import drfLogo from '../../images/django-rest.svg'
import djangoLogo from '../../images/django-logo.png'
import dockerLogo from '../../images/docker-logo-blue.svg'
import postgresqlLogo from '../../images/postgresql.png'
import pythonLogo from '../../images/python-logo.svg'
import reactLogo from '../../images/react-js-logo.png'

const Technologies = () => {

  return <Main>
    <MetaTags>
      <title>О проекте</title>
      <meta name="description" content="Фудграм - Технологии" />
      <meta property="og:title" content="О проекте" />
    </MetaTags>

    <Container>
      <h1 className={styles.title}>Технологии</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Технологии, которые применены в этом проекте:</h2>
          {/* Сетка логотипов 2x3 */}
          <div className={styles.logoGrid}>
            <figure className={styles.logoCard}>
              <img className={styles.logoImg} src={pythonLogo} alt="Python 3" />
              <figcaption className={styles.logoCaption}>Python 3</figcaption>
            </figure>

            <figure className={styles.logoCard}>
              <img className={styles.logoImg} src={djangoLogo} />
              <figcaption className={styles.logoCaption}>Django</figcaption>
            </figure>

            <figure className={styles.logoCard}>
              <img className={styles.logoImg} src={drfLogo} alt="Django REST Framework" />
              <figcaption className={styles.logoCaption}>Django REST Framework</figcaption>
            </figure>

            <figure className={styles.logoCard}>
              <img className={styles.logoImg} src={postgresqlLogo} alt="PostgreSQL" />
              <figcaption className={styles.logoCaption}>PostgreSQL</figcaption>
            </figure>

            <figure className={styles.logoCard}>
              <img className={styles.logoImg} src={reactLogo} alt="React" />
              <figcaption className={styles.logoCaption}>React</figcaption>
            </figure>

            <figure className={styles.logoCard}>
              <img className={styles.logoImg} src={dockerLogo} alt="Docker" />
              <figcaption className={styles.logoCaption}>Docker</figcaption>
            </figure>
          </div>
        </div>
      </div>
    </Container>
  </Main>
}

export default Technologies
