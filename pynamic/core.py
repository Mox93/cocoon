try:
    from faker import Faker
    from extras import ExtraProvider

    fake = Faker()
    fake.add_provider(ExtraProvider)

except ImportError:
    fake = None


__all__ = (fake,)
