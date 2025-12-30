"""Exceptions personnalisées pour Passerelle VHF."""


class VHFBaseException(Exception):
    """Exception de base pour toutes les erreurs VHF."""

    pass


class MeasurementExpiredError(VHFBaseException):
    """Levée quand une mesure est périmée."""

    pass


class ProviderError(VHFBaseException):
    """Erreur lors de la récupération de données depuis un provider."""

    pass


class TTSError(VHFBaseException):
    """Erreur lors de la synthèse vocale."""

    pass


class PTTError(VHFBaseException):
    """Erreur lors du contrôle PTT."""

    pass


class ValidationError(VHFBaseException):
    """Erreur de validation des données."""

    pass


class AuthenticationError(VHFBaseException):
    """Erreur d'authentification."""

    pass
