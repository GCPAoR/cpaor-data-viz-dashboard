resource "aws_vpc" "vpc" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Environment = var.environment
    Name        = "cpaor-vpc-${var.environment}"
  }
}

# Create var.az_count private subnets, each in a different AZ
resource "aws_subnet" "private" {
  count             = var.az_count
  cidr_block        = cidrsubnet(aws_vpc.vpc.cidr_block, 8, count.index)
  availability_zone = var.availability_zones[count.index]
  vpc_id            = aws_vpc.vpc.id
  tags = {
    Environment = var.environment
    Name        = "cpaor-private-subnet-${var.environment}"
  }
}

# Create var.az_count public subnets, each in a different AZ
resource "aws_subnet" "public" {
  count                   = var.az_count
  cidr_block              = cidrsubnet(aws_vpc.vpc.cidr_block, 8, var.az_count + count.index)
  availability_zone       = var.availability_zones[count.index]
  vpc_id                  = aws_vpc.vpc.id
  map_public_ip_on_launch = true
  tags = {
    Environment = var.environment
    Name        = "cpaor-public-subnet-${var.environment}"
  }
}

# Internet Gateway for the public subnet
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags = {
    Environment = var.environment
    Name        = "cpaor-gateway-${var.environment}"
  }
}

# Route the public subnet traffic through the IGW
resource "aws_route" "internet_access" {
  route_table_id         = aws_vpc.vpc.main_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

# Create a NAT gateway with an Elastic IP for each private subnet to get internet connectivity
resource "aws_eip" "eip" {
  count      = 1
  domain     = "vpc"
  depends_on = [aws_internet_gateway.igw]
  tags = {
    Environment = var.environment
    Name        = "cpaor-eip-${var.environment}"
  }
}

resource "aws_nat_gateway" "natgw" {
  count         = 1
  subnet_id     = element(aws_subnet.public.*.id, count.index)
  allocation_id = element(aws_eip.eip.*.id, count.index)
  tags = {
    Environment = var.environment
    Name        = "cpaor-gateway-${var.environment}"
  }
}

# Create a new route table for the private subnets, make it route non-local traffic through the NAT gateway to the internet
resource "aws_route_table" "private" {
  count  = var.az_count
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = element(aws_nat_gateway.natgw.*.id, count.index)
  }
  tags = {
    Environment = var.environment
    Name        = "cpaor-route-table-${var.environment}"
  }
}

# Explicitly associate the newly created route tables to the private subnets (so they don't default to the main route table)
resource "aws_route_table_association" "private" {
  count          = var.az_count
  subnet_id      = element(aws_subnet.private.*.id, count.index)
  route_table_id = element(aws_route_table.private.*.id, count.index)
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id          = aws_vpc.vpc.id
  service_name    = "com.amazonaws.${var.aws_region}.s3"
  route_table_ids = aws_route_table.private.*.id

  tags = {
    Name        = "cpaor-s3-endpoint-${var.environment}"
    Environment = var.environment
  }
}

# resource "aws_vpc_endpoint" "ecr-dkr" {
#   vpc_id          = aws_vpc.vpc.id
#   service_name    = "com.amazonaws.${var.aws_region}.ecr.dkr"
#   route_table_ids = aws_route_table.private.*.id

#   tags = {
#     Name = "ecr-dkr-endpoint-${var.environment}"
#   }
# }

# resource "aws_vpc_endpoint" "ecr-api" {
#   vpc_id          = aws_vpc.vpc.id
#   service_name    = "com.amazonaws.${var.aws_region}.ecr.api"
#   route_table_ids = aws_route_table.private.*.id

#   tags = {
#     Name = "ecr-api-endpoint-${var.environment}"
#   }
# }


# resource "aws_vpc_endpoint" "ecs" {
#   vpc_id          = aws_vpc.vpc.id
#   service_name    = "com.amazonaws.${var.aws_region}.ecs"
#   route_table_ids = aws_route_table.private.*.id

#   tags = {
#     Name = "ssm-endpoint-${var.environment}"
#   }
# }